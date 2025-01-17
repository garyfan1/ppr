<template>
  <v-container class="main-results-div white pa-0 ma-0">
    <!-- Table Header -->
    <article id="search-meta-info" class="px-4 pt-8">
      <v-row no-gutters>
        <span class="search-sub-title">{{ searchType }} - <b>"{{ searchValue }}"</b></span>
        <span class="search-info"> as of {{ searchTime }}</span>
      </v-row>
      <v-row v-if="searched && !isReviewMode" id="search-summary-info" class="result-info pt-6">
        <v-col id="home-results-count" cols="auto">
          <span class="divider pr-3"><b>{{ totalResultsLength }}</b> homes found</span>
        </v-col>
        <v-col id="active-results-count" cols="auto" class="pl-0">
          <span class="divider pr-3"><b>{{ activeMatchesLength }}</b> active homes</span>
        </v-col>
        <v-col cols="auto" class="pl-0">
          <span id="selected-results-count">
            <b>{{ selectedMatchesLength }}</b> homes selected + <b>{{ selectedLiensLength }}</b> lien search
          </span>
        </v-col>
        <v-col class="mt-n3 mr-6">
          <v-row class="float-right">
            <folio-number
              class="mr-3 ml-0 mt-n2"
              :defaultFolioNumber="folioNumber"
              @folio-number="updateFolioOrReference($event)"
              @folio-error="folioError = $event"
            />
            <v-btn
              id="review-confirm-btn"
              color="primary"
              filled
              :disabled="totalResultsLength === 0"
              @click="reviewAndConfirm()"
            >
              Review and Confirm
            </v-btn>
          </v-row>
        </v-col>
      </v-row>
      <v-row v-else class="result-info">
        <v-col id="review-results-count" cols="auto">
          <span><b>{{ selectedMatchesLength }}</b> Manufactured Homes</span>
        </v-col>
      </v-row>
    </article>

    <!-- Search Results Table -->
    <v-row v-if="totalResultsLength !== 0" class="pt-3">
      <v-col cols="12">
        <v-data-table
          v-if="results"
          id="mh-search-results-table"
          class="results-table"
          disable-sort
          fixed
          fixed-header
          group-by="status"
          :headers="headers"
          hide-default-footer
          :items="results"
          item-key="id"
          :items-per-page="-1"
          :item-class="getItemClass"
          mobile-breakpoint="0"
          return-object
        >

          <template  v-if="!isReviewMode" v-slot:[`header.ownerName`]>
            <v-tooltip
              top
              content-class="top-tooltip"
              transition="fade-transition"
              nudge-left="73"
            >
              <template v-slot:activator="{ on, attrs }">
                <span v-bind="attrs" v-on="on">
                  <v-checkbox
                    id="select-all-checkbox"
                    class="header-checkbox ma-0 pa-0"
                    hide-details
                    :label="personOrOrgLabel"
                    v-model="selectAll"
                    @click="onSelectAllClick()"
                  />
                </span>
              </template>
              <div class="pt-2 pb-2">
                Select this to include all manufactured homes.
              </div>
            </v-tooltip>
          </template>

          <template  v-else v-slot:[`header.ownerName`]>
            <span class="pl-8">{{ personOrOrgLabel }}</span>
          </template>

          <template  v-if="!isReviewMode" v-slot:[`header.edit`]>
            <v-checkbox
              id="select-all-lien-checkbox"
              class="header-checkbox ma-0 pa-0"
              hide-details
              label="Include lien information for all selections"
              v-model="selectAllLien"
              :disabled="selectedMatchesLength === 0"
              @click="onSelectAllLienClick()"
            />
          </template>

          <template v-slot:[`group.header`]="{ group }">
            <td
              class="group-header px-4"
              :colspan="headers.length"
            >
              <span v-if="group === 'ACTIVE'">
                <span class="pl-8">
                  ACTIVE HOME REGISTRATIONS ({{ activeMatchesLength }})
                </span>
              </span>
              <span v-else-if="group === 'EXEMPT'" class="pl-8">
                EXEMPT HOME REGISTRATIONS ({{ exemptMatchesLength }})
              </span>
              <span v-else-if="group === 'HISTORIC'" class="pl-8">
                HISTORICAL HOME REGISTRATIONS ({{ historicalMatchesLength }})
              </span>
            </td>
          </template>

          <template v-slot:[`item.ownerName`]="{ item }">
            <v-row class="align-baseline" :class="item.selected && !$props.isReviewMode ? 'selected' : ''">
              <v-col cols="2">
                <v-checkbox v-model="item.selected" @click="onOwnerCheckboxClick(item)"/>
              </v-col>
              <v-col class="owner-name-text" @click="item.selected = !item.selected; onOwnerCheckboxClick(item)">
                {{ getOwnerName(item) }}
              </v-col>
            </v-row>
          </template>
          <template v-slot:[`item.mhrNumber`]="{ item }">
            {{ item.mhrNumber }}
          </template>
          <template v-slot:[`item.state`]="{ item }">
            {{ getOwnerStatus(item.ownerStatus) }}
          </template>
          <template v-if="isReviewMode" v-slot:[`item.yearMakeModel`]="{ item }">
            {{ item.baseInformation.year }} {{ item.baseInformation.make }} {{ item.baseInformation.model }}
          </template>
          <template v-else v-slot:[`item.year`]="{ item }">
            {{ item.baseInformation.year || '-' }}
          </template>
          <template v-slot:[`item.make`]="{ item }">
            {{ item.baseInformation.make || '-' }}
          </template>
          <template v-slot:[`item.model`]="{ item }">
            {{ item.baseInformation.model || '-' }}
          </template>
          <template v-slot:[`item.homeLocation`]="{ item }">
            {{ item.homeLocation }}
          </template>
          <template v-slot:[`item.serialNumber`]="{ item }">
            <span>{{ item.serialNumber }}</span>
          </template>
          <template v-slot:[`item.edit`]="{ item }">
            <v-tooltip
              top
              content-class="top-tooltip"
              transition="fade-transition"
            >
              <template v-slot:activator="{ on, attrs }">
                <span  v-bind="attrs" v-on="on">
                  <v-checkbox
                    :label="`${!isReviewMode ? 'Include lien' : 'Lien'} information`"
                    v-model="item.includeLienInfo"
                    :disabled="!item.selected"
                  />
                </span>
              </template>
              <div class="pt-2 pb-2">
                Select this to include a Personal Property Registry (PPR) lien search for the manufactured home
                for an additional fee.
                You must have the manufactured home selected before you can include the home's lien search.
              </div>
            </v-tooltip>
          </template>
        </v-data-table>
      </v-col>
    </v-row>
    <v-row v-else id="search-no-results-info" class="no-results-info pb-10" justify="center">
      <v-col cols="8">
        <p class="no-results-title ma-0 pt-10"><b>Nil Result</b></p>
        <p class="ma-0 pt-2">
          No registered homes can be found to match the
          search criteria above.
        </p>
      </v-col>
    </v-row>
  </v-container>
</template>

<script lang="ts">
import { computed, defineComponent, reactive, toRefs, onMounted, watch } from '@vue/composition-api'
import { useActions, useGetters } from 'vuex-composition-helpers' // eslint-disable-line no-unused-vars

import { manufacturedHomeSearchTableHeaders, manufacturedHomeSearchTableHeadersReview } from '@/resources'
import { BaseHeaderIF, ManufacturedHomeSearchResultIF } from '@/interfaces' // eslint-disable-line no-unused-vars
import { FolioNumber } from '@/components/common'
import { pacificDate } from '@/utils'
import { APIMHRMapSearchTypes, RouteNames } from '@/enums'
import { cloneDeep } from 'lodash'

export default defineComponent({
  components: {
    FolioNumber
  },
  props: {
    isReviewMode: { default: false }
  },
  setup (props, context) {
    const {
      getManufacturedHomeSearchResults,
      getFolioOrReferenceNumber,
      getSearchedType,
      getSelectedManufacturedHomes
    } = useGetters<any>([
      'getManufacturedHomeSearchResults', 'getFolioOrReferenceNumber', 'getSearchedType', 'getSelectedManufacturedHomes'
    ])
    const { setSelectedManufacturedHomes, setFolioOrReferenceNumber } = useActions<any>([
      'setSelectedManufacturedHomes', 'setFolioOrReferenceNumber'
    ])
    const router = context.root.$router

    const localState = reactive({
      searched: false,
      searchValue: '',
      searchTime: '',
      searchType: null,
      selectAll: false,
      selectAllLien: false,
      folioNumber: getFolioOrReferenceNumber.value,
      tooltipTxtSrchMtchs: 'One or more of the selected matches appear in ' +
        'the same registration. That registration will only be shown once in the report.',
      results: [],
      totalResultsLength: 0,
      activeMatchesLength: computed((): number => {
        return localState.results?.filter(item => item.status === 'ACTIVE').length
      }),
      selectedMatchesLength: computed((): number => {
        return localState.results?.filter(item => item.selected === true).length
      }),
      selectedLiensLength: computed((): number => {
        return localState.results?.filter(item => item.includeLienInfo === true).length
      }),
      exemptMatchesLength: computed((): number => {
        return localState.results?.filter(item => item.status === 'EXEMPT').length
      }),
      historicalMatchesLength: computed((): number => {
        return localState.results?.filter(item => item.status === 'HISTORIC').length
      }),
      headers: computed((): Array<BaseHeaderIF> => {
        return props.isReviewMode ? manufacturedHomeSearchTableHeadersReview : manufacturedHomeSearchTableHeaders
      }),
      personOrOrgLabel: computed((): string => {
        return getManufacturedHomeSearchResults.value.searchQuery.type === APIMHRMapSearchTypes.MHRORGANIZATION_NAME
          ? 'Organization Name'
          : 'Owner Name'
      }),
      areAllSelected: computed((): boolean => {
        return localState.results?.every(result => result && result.selected === true)
      }),
      activeResults: computed((): any => {
        const selectedResults = cloneDeep(getSelectedManufacturedHomes).value
        const baseResults = cloneDeep(getManufacturedHomeSearchResults.value.results)

        // Map selected results with base results when user navigates back to edit selections further
        const activeResults = baseResults?.map(result => {
          const matchedResult = selectedResults?.find(({ id }) => id === result.id)
          return {
            ...result,
            ...(matchedResult && {
              selected: matchedResult.selected,
              includeLienInfo: matchedResult.includeLienInfo
            })
          }
        })

        return props.isReviewMode
          ? selectedResults
          : activeResults
      })
    })

    const reviewAndConfirm = (): void => {
      router.push({ name: RouteNames.MHRSEARCH_CONFIRM })
    }

    const getOwnerName = (item: ManufacturedHomeSearchResultIF): string => {
      if (item.ownerName) {
        return `
          ${item.ownerName?.last},
          ${item.ownerName?.first}
          ${item.ownerName?.middle || item.ownerName?.second || ''}`
      } else if (item.organizationName) {
        return item.organizationName
      } else return '-'
    }

    const getItemClass = (item: ManufacturedHomeSearchResultIF): string => {
      return item.selected && !props.isReviewMode ? 'selected' : ''
    }

    const onOwnerCheckboxClick = (item: ManufacturedHomeSearchResultIF): void => {
      if (!item.selected) {
        item.includeLienInfo = false
      }
      if (item.selected && localState.selectAllLien) {
        item.includeLienInfo = true
      }
    }

    const getOwnerStatus = (ownerStatus: string): string => {
      if (ownerStatus) {
        if (ownerStatus === 'PREVIOUS') return 'HISTORICAL'
        else return ownerStatus
      } else return ''
    }

    const updateFolioOrReference = (folioOrReference: string): void => {
      setFolioOrReferenceNumber(folioOrReference)
    }

    onMounted(async () => {
      const resp = getManufacturedHomeSearchResults.value
      if (!resp) await router.push({ name: RouteNames.DASHBOARD })

      localState.searchValue = resp.searchQuery.criteria.value || getOwnerName(resp.searchQuery.criteria)
      localState.searched = true
      localState.searchType = getSearchedType.value?.searchTypeUI || ''
      localState.results = sortByStatus(localState.activeResults)
      localState.results = localState.results.map(result => {
        // includeLienInfo needs to be initialized or something weird will happen
        return result.includeLienInfo !== true ? { ...result, includeLienInfo: false } : result
      })
      localState.totalResultsLength = resp.totalResultsSize
      const date = new Date(resp.searchDateTime)
      localState.searchTime = pacificDate(date)
    })

    /** Custom sorting method to handle results by status. */
    const sortByStatus = (items: Array<ManufacturedHomeSearchResultIF> = []): Array<ManufacturedHomeSearchResultIF> => {
      items.sort((a, b) => {
        if (a.status < b.status) {
          return -1
        }
        if (a.status > b.status) {
          return 1
        }
        return 0
      })
      return items
    }

    watch(() => localState.results, (): void => {
      const selectedManufacturedHomes = cloneDeep(localState.results?.filter(result => result.selected === true))
      setSelectedManufacturedHomes(selectedManufacturedHomes)
      localState.selectAll = localState.results.every(result => result.selected)
      if (localState.selectedMatchesLength === 0) {
        localState.selectAllLien = false
      }
    }, { deep: true })

    const onSelectAllClick = (): void => {
      const val = localState.selectAll
      localState.results = localState.results.map(result => ({ ...result, selected: val }))
      if (val && localState.selectAllLien) {
        localState.results = localState.results.map(result => ({ ...result, includeLienInfo: val }))
      }
      if (!val) {
        localState.results = localState.results.map(result => ({ ...result, includeLienInfo: val }))
      }
    }

    const onSelectAllLienClick = (): void => {
      for (const result of localState.results) {
        if (result.selected) {
          result.includeLienInfo = localState.selectAllLien
        }
      }
    }

    return {
      reviewAndConfirm,
      getOwnerName,
      getOwnerStatus,
      updateFolioOrReference,
      getItemClass,
      onOwnerCheckboxClick,
      onSelectAllClick,
      onSelectAllLienClick,
      ...toRefs(localState)
    }
  }
})
</script>

<style lang="scss" scoped>
@import '@/assets/styles/theme.scss';
button {
  font-weight: normal !important;
}
td {
  font-size: 0.875rem !important;
  color: $gray7 !important;
}
th {
  font-size: 0.875rem !important;
  color: $gray9 !important;
}
.checkbox-info {
  font-size: 0.725rem !important;
  font-weight: bold;
  text-align: center;
}
.divider {
  border-right: 1px solid $gray3;
}
#review-confirm-btn {
  min-width: 260px;
  font-weight: 600 !important;
}
.group-header, .group-header:hover {
  background-color: $gray3;
  font-weight: bold;
}
.main-results-div {
  width: 100%;
}
.owner-name-text {
  cursor: pointer;
}
.no-results-info {
  color: $gray7 !important;
  font-size: 1rem;
  text-align: center;
}
.no-results-title {
  font-size: 1.125rem;
}
.result-info {
  color: $gray7 !important;
  font-size: 1rem;
}
::v-deep {
  .header-checkbox .v-input__control .v-input__slot .v-label {
    color: $gray9;
    font-size: 0.875rem !important;
    font-weight: bold;
  }
  .v-input__control .v-input--selection-controls__input i { //checkbox border color
    color: $primary-blue !important;
  }
  // disabled checkbox border color
  .v-input--selection-controls.v-input--is-disabled:not(.v-input--indeterminate) .v-icon {
    // primary blue 40% opacity
    color: #1669bb28 !important;
  }
  .v-label--is-disabled { // disabled label
    color: #757575;
  }
  .results-table .lien-info {
    width: 100%;
  }
  .results-table .v-input--checkbox .v-input__slot .v-label {
    font-size: 0.875rem !important;
  }
  .results-table .v-data-table__wrapper {
    max-height: 550px;
  }
  .results-table .v-data-table__wrapper table tbody {
    .v-input--selection-controls .v-input__slot, .v-input--selection-controls .v-radio {
      align-items: baseline;
    }
    tr {
      height: 54px;
      td:not(.group-header) {
        display: table-cell;
        vertical-align: baseline;
        overflow: hidden;
        white-space: normal;
      }
      td:not(:last-child) {
        word-break: break-word;
      }
    }
    .selected {
      background-color: $blueSelected !important;
    }
    tr:hover:not(.selected) {
      // $gray1 at 75%
      background-color: #f1f3f5BF !important;
    }
  }
}
</style>
