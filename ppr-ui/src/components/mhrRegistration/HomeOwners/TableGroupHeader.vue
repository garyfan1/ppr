<template>
  <div :id="'mhr-home-edit-owners-group-' + groupId" class="group-header">
    <BaseDialog
      :setDisplay="showDeleteGroupDialog"
      @proceed="cancelOrProceed($event, groupId)"
      :setOptions="{
        title: 'Delete Group',
        text:
          'Deleting a group also deletes all of the owners in the group and cannot be undone. ' +
          'All subsequent groups will be re-numbered.' +
          '<br><br>' +
          'If you wish to keep the owners of this group move the ' +
          'owners to a different group prior to deletion.',
        acceptText: 'Delete Group',
        cancelText: 'Cancel'
      }"
    />
    <div v-if="!isEditGroupMode" class="group-header-summary">
      <div>
        <span class="mr-2 font-weight-bold">Group {{ groupId }}</span>
        |
        <span class="ma-2">Owners: {{ owners.length }} </span>
        |
        <span class="ma-2">Group Tenancy Type: </span>
        |
        <span class="ma-2"> Interest: {{ getOwnershipInterest() }} </span>
      </div>

      <div>
        <v-btn
          text
          color="primary"
          class="pr-0"
          :ripple="false"
          :disabled="isGlobalEditingMode"
          @click="openGroupForEditing(groupId)"
        >
          <v-icon small>mdi-pencil</v-icon>
          <span>Edit</span>
          <v-divider class="ma-0 pl-3" vertical />
        </v-btn>

        <v-menu offset-y left nudge-bottom="0" class="delete-group-menu">
          <template v-slot:activator="{ on }">
            <v-btn text v-on="on" color="primary" class="pa-0" :disabled="isGlobalEditingMode">
              <v-icon>mdi-menu-down</v-icon>
            </v-btn>
          </template>

          <!-- More actions drop down list -->
          <v-list class="actions-dropdown actions__more-actions">
            <v-list-item class="my-n2">
              <v-list-item-subtitle class="pa-0" @click="showDeleteGroupDialog = true">
                <v-icon small style="margin-bottom: 3px;">mdi-delete</v-icon>
                <span class="ml-1 remove-btn-text">Delete Group</span>
              </v-list-item-subtitle>
            </v-list-item>
          </v-list>
        </v-menu>
      </div>
    </div>
    <div v-else>
      <v-row>
        <v-col cols="3">
          <label class="generic-label"> Edit Group </label>
        </v-col>
        <v-col cols="9">
          <label class="generic-label"> Group {{ groupId }} Details: </label>

          <v-form class="my-5" ref="homeFractionalOwnershipForm" v-model="isHomeFractionalOwnershipValid">
            <FractionalOwnership :groupId="groupId" :fractionalData="fractionalData" />
          </v-form>
        </v-col>
      </v-row>
      <v-row>
        <v-col>
          <div class="form__row form__btns">
            <v-btn color="primary" class="ml-auto" :ripple="false" large @click="done()">
              Done
            </v-btn>
            <v-btn :ripple="false" large color="primary" outlined @click="cancel()">
              Cancel
            </v-btn>
          </div>
        </v-col>
      </v-row>
    </div>
  </div>
</template>

<script lang="ts">
import { BaseDialog } from '@/components/dialogs'
import { useHomeOwners } from '@/composables/mhrRegistration'
import { defineComponent, reactive, ref, toRefs, watch } from '@vue/composition-api'
import FractionalOwnership from './FractionalOwnership.vue'
import { useGetters } from 'vuex-composition-helpers'
import { find } from 'lodash'
/* eslint-disable no-unused-vars */
import { MhrRegistrationFractionalOwnershipIF } from '@/interfaces/mhr-registration-interfaces'
/* eslint-enable no-unused-vars */

export default defineComponent({
  name: 'TableGroupHeader',
  props: {
    groupId: { default: '' },
    owners: { default: [] }
  },
  components: {
    BaseDialog,
    FractionalOwnership
  },
  setup (props, context) {
    const { getMhrRegistrationHomeOwnerGroups } = useGetters<any>(['getMhrRegistrationHomeOwnerGroups'])

    const { isGlobalEditingMode, setGlobalEditingMode, deleteGroup, setGroupFractionalInterest } = useHomeOwners()

    const homeFractionalOwnershipForm = ref(null)

    const localState = reactive({
      isEditGroupMode: false,
      showDeleteGroupDialog: false,
      isHomeFractionalOwnershipValid: false,
      group: find(getMhrRegistrationHomeOwnerGroups.value, { groupId: props.groupId }),
      fractionalData: {} as MhrRegistrationFractionalOwnershipIF
    })

    const openGroupForEditing = (): void => {
      localState.fractionalData = {
        type: localState.group?.type || '',
        interest: localState.group?.interest || '',
        interestNumerator: localState.group?.interestNumerator || null,
        interestTotal: localState.group?.interestTotal || null,
        tenancySpecified: localState.group?.tenancySpecified || null
      } as MhrRegistrationFractionalOwnershipIF

      localState.isEditGroupMode = true
    }

    const getOwnershipInterest = (): string => {
      const { interest, interestNumerator, interestTotal } = localState.group

      return `${interest} ${interestNumerator}/${interestTotal}`
    }

    const done = (): void => {
      // @ts-ignore - function exists
      context.refs.homeFractionalOwnershipForm.validate()

      if (localState.isHomeFractionalOwnershipValid) {
        localState.isEditGroupMode = false
        setGroupFractionalInterest(props.groupId, localState.fractionalData)
      }
    }

    const cancel = (): void => {
      localState.isEditGroupMode = false
      localState.group = find(getMhrRegistrationHomeOwnerGroups.value, { groupId: props.groupId })
    }

    watch(
      () => localState.isEditGroupMode,
      () => {
        setGlobalEditingMode(localState.isEditGroupMode)
      }
    )

    // Close Delete Group dialog or proceed to deleting a Group
    const cancelOrProceed = (proceed: boolean, groupId: string): void => {
      if (proceed) {
        deleteGroup(groupId)
        localState.showDeleteGroupDialog = false
      } else {
        localState.showDeleteGroupDialog = false
      }
    }

    return {
      getOwnershipInterest,
      openGroupForEditing,
      isGlobalEditingMode,
      done,
      cancel,
      cancelOrProceed,
      homeFractionalOwnershipForm,
      ...toRefs(localState)
    }
  }
})
</script>

<style lang="scss" scoped>
.group-header::v-deep {
  .group-header-summary {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
}
</style>
