import { reactive, toRefs, computed } from '@vue/composition-api'
import { PartyIF, AddressIF } from '@/interfaces' // eslint-disable-line no-unused-vars
import { useGetters, useActions } from 'vuex-composition-helpers'
import { PartyAddressSchema } from '@/schemas'
import { ActionTypes, APIRegistrationTypes, RegistrationFlowType } from '@/enums'
import { checkAddress, formatAddress } from '@/composables/address/factories/address-factory'
import { cloneDeep, isEqual } from 'lodash'
import { useParty } from '@/composables/useParty'

const initPerson = { first: '', middle: '', last: '' }
const initAddress = {
  street: '',
  streetAdditional: '',
  city: '',
  region: '',
  country: '',
  postalCode: '',
  deliveryInstructions: ''
}
const { isPartiesValid } = useParty()

export const useSecuredParty = (props, context) => {
  const { setAddSecuredPartiesAndDebtors } = useActions<any>([
    'setAddSecuredPartiesAndDebtors'
  ])
  const { getAddSecuredPartiesAndDebtors, getRegistrationFlowType, getRegistrationType } = useGetters<any>([
    'getAddSecuredPartiesAndDebtors', 'getRegistrationFlowType', 'getRegistrationType'
  ])
  const localState = reactive({
    currentSecuredParty: {
      businessName: '',
      personName: initPerson,
      emailAddress: '',
      address: initAddress
    } as PartyIF,
    currentIsBusiness: null,
    partyBusiness: null,
    registrationFlowType: getRegistrationFlowType.value,
    originalSecuredParty: null
  })

  const getSecuredParty = (isRegisteringParty) => {
    const securedParties: PartyIF[] =
      getAddSecuredPartiesAndDebtors.value.securedParties
    const registeringParty: PartyIF = getAddSecuredPartiesAndDebtors.value.registeringParty
    if (isRegisteringParty && registeringParty && registeringParty.action && !registeringParty.code) {
      // copy the existing registering party
      localState.currentSecuredParty = JSON.parse(JSON.stringify(registeringParty))
      localState.currentSecuredParty.address = checkAddress(localState.currentSecuredParty.address, PartyAddressSchema)
      localState.currentIsBusiness = false
      localState.partyBusiness = 'I'
      if (localState.currentSecuredParty.businessName) {
        localState.currentIsBusiness = true
        localState.partyBusiness = 'B'
        localState.currentSecuredParty.personName = Object.assign({}, initPerson)
      }
    } else if (props.activeIndex >= 0) {
      // deep copy so original object doesn't get modified
      localState.currentSecuredParty = JSON.parse(JSON.stringify(securedParties[props.activeIndex]))
      localState.currentSecuredParty.address = checkAddress(localState.currentSecuredParty.address, PartyAddressSchema)
      localState.currentIsBusiness = false
      localState.partyBusiness = 'I'
      if (localState.currentSecuredParty.businessName) {
        localState.currentIsBusiness = true
        localState.partyBusiness = 'B'
        localState.currentSecuredParty.personName = Object.assign({}, initPerson)
      }
    } else {
      localState.partyBusiness = null
      const blankSecuredParty = {
        businessName: '',
        personName: Object.assign({}, initPerson),
        birthDate: '',
        emailAddress: '',
        address: Object.assign({}, initAddress)
      }
      localState.currentSecuredParty = blankSecuredParty
    }
    localState.originalSecuredParty = cloneDeep(localState.currentSecuredParty)
  }

  const addressSchema = PartyAddressSchema

  const resetFormAndData = (emitEvent: boolean): void => {
    if (emitEvent) {
      context.emit('resetEvent')
    }
  }

  const isExistingSecuredParty = (partyCode: string): boolean => {
    let parties = getAddSecuredPartiesAndDebtors.value // eslint-disable-line
    const idx = parties.securedParties.findIndex(party =>
      party.code === partyCode
    )
    return idx !== -1
  }

  const removeSecuredParty = (): void => {
    context.emit('removeSecuredParty', props.activeIndex)
    resetFormAndData(true)
  }

  const addEditSecuredParty = async () => {
    let parties = getAddSecuredPartiesAndDebtors.value // eslint-disable-line
    let newList: PartyIF[] = parties.securedParties // eslint-disable-line
    if (!localState.currentSecuredParty.businessName) {
      delete localState.currentSecuredParty.businessName
    }

    // first format the original address
    // if they didn't change anything, just exit
    if (localState.originalSecuredParty) {
      localState.originalSecuredParty.address = formatAddress(localState.originalSecuredParty.address)
    }
    if ((localState.registrationFlowType === RegistrationFlowType.AMENDMENT) &&
    isEqual(localState.currentSecuredParty, localState.originalSecuredParty)) {
      resetFormAndData(true)
      return
    }
    // New secured party
    if (props.activeIndex === -1) {
      localState.currentSecuredParty.action = ActionTypes.ADDED
      newList.push(localState.currentSecuredParty)
    } else {
      // Edit party
      if (!localState.currentSecuredParty.action) {
        localState.currentSecuredParty.action = ActionTypes.EDITED
      }
      newList.splice(props.activeIndex, 1, localState.currentSecuredParty)
    }
    parties.securedParties = newList
    setAddSecuredPartiesAndDebtors(parties)
    context.emit('resetEvent')
  }

  const setRegisteringParty = (registeringParty: PartyIF) => {
    let parties = getAddSecuredPartiesAndDebtors.value // eslint-disable-line
    registeringParty.action = ActionTypes.EDITED
    parties.registeringParty = registeringParty
    parties.valid = isPartiesValid(parties, getRegistrationType.value.registrationTypeAPI)
    setAddSecuredPartiesAndDebtors(parties)
  }

  const addSecuredParty = (newParty: PartyIF) => {
    let parties = getAddSecuredPartiesAndDebtors.value // eslint-disable-line
    let newList: PartyIF[] = parties.securedParties // eslint-disable-line
    newParty.action = ActionTypes.ADDED
    newList.push(newParty)
    parties.securedParties = newList
    parties.valid = isPartiesValid(parties, getRegistrationType.value.registrationTypeAPI)
    setAddSecuredPartiesAndDebtors(parties)
  }

  /**
   * Handles update events from address sub-components.
   */
  const updateAddress = (newAddress: AddressIF): void => {
    localState.currentSecuredParty.address = newAddress
  }

  return {
    getSecuredParty,
    addEditSecuredParty,
    resetFormAndData,
    removeSecuredParty,
    addressSchema,
    updateAddress,
    addSecuredParty,
    isExistingSecuredParty,
    RegistrationFlowType,
    ActionTypes,
    setRegisteringParty,
    ...toRefs(localState)
  }
}
