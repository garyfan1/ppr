<template>
  <div id="mhr-review-confirm">
    <!-- Review and Confirm -->
    <div class="mt-10">
      <h2>Review and Confirm</h2>
      <p class="mt-4">
        Review the information in your registration and complete the additional information below. If you need to
        change anything, return to the previous step to make the necessary change.
      </p>

      <!-- Your Home Summary -->
      <YourHomeReview />

      <!-- Submitting Party Review -->
      <SubmittingPartyReview />

      <!-- Home Location Review -->
      <HomeLocationReview />
    </div>

    <!-- Authorization -->
    <section id="certify-section" class="mt-10">
      <article>
        <h2>Authorization</h2>
        <p class="mt-4">
          The following account information will be recorded by BC Registries upon registration and payment. This
          information is used to confirm you have the authority to submit this registration and will not appear on the
          verification statement.
        </p>
      </article>

      <v-card flat class="mt-6">
        <!-- Certify Placeholder -->
      </v-card>
    </section>

    <!-- Staff Payment -->
    <section id="staff-payment-section" class="mt-10" v-if="true">
      <article>
        <h2>Staff Payment</h2>
        <p class="mt-4"></p>
      </article>

      <v-card flat class="mt-6 pa-6">
        <!-- Staff Payment Piece -->
        <staff-payment-component
          id="staff-payment-card"
          :staffPaymentData="staffPaymentData"
          :validate="validatingStaffPayment"
          :displaySideLabel="true"
          :displayPriorityCheckbox="true"
          :invalidSection="false"
          @update:staffPaymentData="onStaffPaymentDataUpdate($event)"
          @valid="staffPaymentValid = $event"
        />
      </v-card>
    </section>
  </div>
</template>

<script lang="ts">
import { defineComponent, onMounted, reactive, toRefs, watch } from '@vue/composition-api'
import { HomeLocationReview, SubmittingPartyReview, YourHomeReview } from '@/components/mhrRegistration/ReviewConfirm'
import { useMhrValidations } from '@/composables'
import { RouteNames } from '@/enums'
import { useGetters, useActions } from 'vuex-composition-helpers'
import { StaffPayment as StaffPaymentComponent } from '@bcrs-shared-components/staff-payment'
import { StaffPaymentOptions } from '@bcrs-shared-components/enums'
// eslint-disable-next-line no-unused-vars
import { StaffPaymentIF } from '@bcrs-shared-components/interfaces'

export default defineComponent({
  name: 'MhrReviewConfirm',
  components: {
    YourHomeReview,
    SubmittingPartyReview,
    HomeLocationReview,
    StaffPaymentComponent
  },
  props: {},
  setup (props, context) {
    const {
      getMhrRegistrationValidationModel,
      getStaffPayment
    } = useGetters<any>([
      'getMhrRegistrationValidationModel',
      'getStaffPayment'
    ])

    const {
      setStaffPayment
    } = useActions<any>([
      'setStaffPayment'
    ])

    const {
      MhrCompVal,
      MhrSectVal,
      setValidation,
      scrollToInvalid,
      getStepValidation
    } = useMhrValidations(toRefs(getMhrRegistrationValidationModel.value))

    const localState = reactive({
      staffPaymentData: {
        option: StaffPaymentOptions.NONE,
        routingSlipNumber: '',
        bcolAccountNumber: '',
        datNumber: '',
        folioNumber: '',
        isPriority: false
      },
      staffPaymentValid: null,
      validatingStaffPayment: false
    })

    onMounted(() => {
      if (getStaffPayment.value) {
        localState.staffPaymentData = { ...getStaffPayment.value }
      }
    })

    const onStaffPaymentDataUpdate = (val: StaffPaymentIF) => {
      let staffPaymentData: StaffPaymentIF = {
        ...val
      }

      // disable validation
      switch (staffPaymentData.option) {
        case StaffPaymentOptions.FAS:
          staffPaymentData = {
            option: StaffPaymentOptions.FAS,
            routingSlipNumber: staffPaymentData.routingSlipNumber,
            isPriority: staffPaymentData.isPriority,
            bcolAccountNumber: '',
            datNumber: '',
            folioNumber: ''
          }
          break

        case StaffPaymentOptions.BCOL:
          staffPaymentData = {
            option: StaffPaymentOptions.BCOL,
            bcolAccountNumber: staffPaymentData.bcolAccountNumber,
            datNumber: staffPaymentData.datNumber,
            folioNumber: staffPaymentData.folioNumber,
            isPriority: staffPaymentData.isPriority,
            routingSlipNumber: ''
          }
          break

        case StaffPaymentOptions.NO_FEE:
          staffPaymentData = {
            option: StaffPaymentOptions.NO_FEE,
            routingSlipNumber: '',
            isPriority: false,
            bcolAccountNumber: '',
            datNumber: '',
            folioNumber: ''
          }
          break

        case StaffPaymentOptions.NONE: // should never happen
          break
      }

      setStaffPayment(staffPaymentData)
    }

    watch(() => context.root.$route.name, (route: string) => {
      switch (route) {
        case RouteNames.YOUR_HOME:
          scrollToInvalid(MhrSectVal.YOUR_HOME_VALID, 'mhr-describe-your-home')
          break
        case RouteNames.SUBMITTING_PARTY:
          scrollToInvalid(MhrSectVal.SUBMITTING_PARTY_VALID, 'mhr-submitting-party')
          break
        case RouteNames.HOME_OWNERS:
          scrollToInvalid(MhrSectVal.HOME_OWNERS_VALID, 'mhr-home-owners-list')
          break
        case RouteNames.HOME_LOCATION:
          scrollToInvalid(MhrSectVal.LOCATION_VALID, 'mhr-home-location')
          break
        case RouteNames.MHR_REVIEW_CONFIRM:
          scrollToInvalid(MhrSectVal.REVIEW_CONFIRM_VALID, 'mhr-review-confirm',
            [
              getStepValidation(MhrSectVal.YOUR_HOME_VALID),
              getStepValidation(MhrSectVal.SUBMITTING_PARTY_VALID),
              getStepValidation(MhrSectVal.HOME_OWNERS_VALID),
              getStepValidation(MhrSectVal.LOCATION_VALID)
            ])
          setValidation(MhrSectVal.REVIEW_CONFIRM_VALID, MhrCompVal.VALIDATE_STEPS, true)
          break
      }
    })

    return {
      onStaffPaymentDataUpdate,
      ...toRefs(localState)
    }
  }
})
</script>

<style lang="scss" scoped>
@import '@/assets/styles/theme.scss';
</style>
